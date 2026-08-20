import React from "react";
import { Loader2 } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  isLoading?: boolean;
}

export function Button({ 
  children, 
  variant = "primary", 
  isLoading = false, 
  className,
  disabled,
  ...props 
}: ButtonProps) {
  
  const baseStyles = "inline-flex items-center justify-center rounded-lg font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-background disabled:opacity-50 disabled:cursor-not-allowed";
  
  const variants = {
    primary: "bg-primary text-white hover:bg-primary-hover shadow-lg shadow-primary/20 hover:shadow-primary/40 focus:ring-primary",
    secondary: "bg-surface border border-surface-border text-foreground hover:bg-white/5 focus:ring-white/20",
    ghost: "bg-transparent text-gray-400 hover:text-white hover:bg-white/10 focus:ring-white/20"
  };

  return (
    <button
      className={cn(baseStyles, variants[variant], "px-4 py-2", className)}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
      {children}
    </button>
  );
}
