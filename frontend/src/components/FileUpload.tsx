import React, { useCallback, useState } from "react";
import { FileUp, File as FileIcon, X } from "lucide-react";
import { cn, Button } from "./ui/Button";

interface FileUploadProps {
  onUpload: (file: File) => void;
  isLoading: boolean;
}

export function FileUpload({ onUpload, isLoading }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const validateAndSelectFile = useCallback((file: File) => {
    if (file.size > 20 * 1024 * 1024) {
      setError("File is too large. Max size is 20MB.");
      return;
    }
    if (!file.type.includes("pdf") && !file.type.includes("image")) {
      setError("Only PDFs and Images are supported.");
      return;
    }
    setSelectedFile(file);
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    setError(null);

    const file = e.dataTransfer.files[0];
    if (file) validateAndSelectFile(file);
  }, [validateAndSelectFile]);

  const onFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    if (e.target.files && e.target.files[0]) {
      validateAndSelectFile(e.target.files[0]);
    }
  }, [validateAndSelectFile]);

  const handleUploadClick = () => {
    if (selectedFile) {
      onUpload(selectedFile);
    }
  };

  return (
    <div className="w-full max-w-xl mx-auto">
      {!selectedFile ? (
        <label 
          className={cn(
            "glass-panel flex flex-col items-center justify-center w-full h-64 rounded-2xl cursor-pointer transition-all duration-300 border-2 border-dashed",
            isDragging ? "border-primary bg-primary/5" : "border-surface-border hover:border-gray-400"
          )}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
        >
          <div className="flex flex-col items-center justify-center pt-5 pb-6 text-center px-4">
            <div className="p-4 bg-surface rounded-full mb-4 shadow-lg">
              <FileUp className="w-8 h-8 text-primary" />
            </div>
            <p className="mb-2 text-lg font-semibold">Click to upload or drag and drop</p>
            <p className="text-sm text-gray-400">PDF, JPG, PNG or TIFF (MAX. 20MB)</p>
          </div>
          <input 
            type="file" 
            className="hidden" 
            accept=".pdf,image/*" 
            onChange={onFileChange}
          />
        </label>
      ) : (
        <div className="glass-panel p-6 rounded-2xl animate-fade-in">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-primary/20 rounded-lg text-primary">
                <FileIcon className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm font-medium truncate max-w-[200px] sm:max-w-[300px]">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-gray-400">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <button 
              onClick={() => setSelectedFile(null)}
              className="p-2 text-gray-400 hover:text-white transition-colors"
              disabled={isLoading}
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          <Button 
            className="w-full" 
            onClick={handleUploadClick}
            isLoading={isLoading}
          >
            {isLoading ? "Processing..." : "Analyze Document"}
          </Button>
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-sm text-center animate-slide-up">
          {error}
        </div>
      )}
    </div>
  );
}
