import { Lease, UploadResponse } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function uploadLease(file: File): Promise<UploadResponse> {
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
