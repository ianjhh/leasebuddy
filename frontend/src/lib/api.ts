import { Lease, UploadResponse } from "./types";
import { DEMO_LEASE, IS_DEMO } from "./demo";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function uploadLease(file: File): Promise<UploadResponse> {
  if (IS_DEMO) {
    throw new Error("Uploads are disabled in the demo. Open the sample lease instead.");
  }

  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/leases/`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to upload file");
  }

  return response.json();
}

export async function getLease(leaseId: string): Promise<Lease> {
  if (IS_DEMO) {
    if (leaseId !== DEMO_LEASE.id) throw new Error("Failed to fetch lease data");
    return DEMO_LEASE;
  }

  const response = await fetch(`${API_BASE_URL}/leases/${leaseId}`);
  
  if (!response.ok) {
    throw new Error("Failed to fetch lease data");
  }

  return response.json();
}

export async function deleteLease(leaseId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/leases/${leaseId}`, {
    method: "DELETE",
  });
  
  if (!response.ok) {
    throw new Error("Failed to delete lease");
  }
}
