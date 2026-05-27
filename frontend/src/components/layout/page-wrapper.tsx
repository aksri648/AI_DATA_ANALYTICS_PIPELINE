import type { ReactNode } from "react";

interface PageWrapperProps {
  title: string;
  description?: string;
  children: ReactNode;
}

export function PageWrapper({ title, description, children }: PageWrapperProps) {
  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:p-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      {children}
    </div>
  );
}
