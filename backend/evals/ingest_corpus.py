"""
Ingests the generated corpus into Postgres through the production indexer.

Uses app.rag.indexer.index_document, so chunking, embedding and page metadata
are exactly what the running system produces. Also creates the schema, which is
what puts the HNSW index in place.

Run:  python -m evals.ingest_corpus
Out:  tests/evaluation/data/ingested_lease_ids.json
"""

import asyncio
import json
import uuid
from pathlib import Path

from sqlalchemy import text

from app.db.session import AsyncSessionLocal, engine
from app.models.base import Base
from app.models.lease import LeaseDocument
from app.rag.indexer import index_document

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "tests" / "evaluation" / "data"


async def main() -> None:
    corpus = json.loads((DATA / "corpus.json").read_text(encoding="utf-8"))

    print("Creating schema (this is what creates the HNSW index)...")
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    # Start from a clean slate so repeated runs stay comparable.
    async with AsyncSessionLocal() as db:
        await db.execute(text("DELETE FROM lease_chunks"))
        await db.execute(text("DELETE FROM lease_documents"))
        await db.commit()

    lease_ids: dict[str, str] = {}
    total_chunks = 0

    for lease in corpus:
        lease_id = uuid.uuid4()
        async with AsyncSessionLocal() as db:
            db.add(LeaseDocument(
                id=lease_id,
                filename=f"lease_{lease['lease_index']}.pdf",
                status="processing",
                metadata_={"page_count": len(lease["pages"]),
                           "lease_index": lease["lease_index"]},
            ))
            await db.commit()

            count = await index_document(str(lease_id), lease["pages"], db)

            await db.execute(
                text("UPDATE lease_documents SET status='completed' WHERE id=:i"),
                {"i": str(lease_id)},
            )
            await db.commit()

        lease_ids[str(lease["lease_index"])] = str(lease_id)
        total_chunks += count
        print(f"  lease {lease['lease_index']}: {len(lease['pages'])} pages -> {count} chunks")

    (DATA / "ingested_lease_ids.json").write_text(json.dumps(lease_ids, indent=2), encoding="utf-8")
    print(f"\nIngested {len(corpus)} leases, {total_chunks} chunks total.")
    print(f"Lease ids written to {DATA / 'ingested_lease_ids.json'}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
