import * as React from "react";

import { cn } from "@/lib/utils";

export function Table({ className, ...props }: React.TableHTMLAttributes<HTMLTableElement>): JSX.Element {
  return (
    <div className="w-full overflow-auto">
      <table className={cn("w-full caption-bottom text-sm", className)} {...props} />
    </div>
  );
}

export function TableHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLTableSectionElement>): JSX.Element {
  return <thead className={cn("[&_tr]:border-b", className)} {...props} />;
}

export function TableBody({
  className,
  ...props
}: React.HTMLAttributes<HTMLTableSectionElement>): JSX.Element {
  return <tbody className={cn("[&_tr:last-child]:border-0", className)} {...props} />;
}

export function TableRow({ className, ...props }: React.HTMLAttributes<HTMLTableRowElement>): JSX.Element {
  return <tr className={cn("border-b transition-colors hover:bg-slate-50", className)} {...props} />;
}

export function TableHead({
  className,
  ...props
}: React.ThHTMLAttributes<HTMLTableCellElement>): JSX.Element {
  return <th className={cn("h-10 px-2 text-left align-middle font-medium text-slate-600", className)} {...props} />;
}

export function TableCell({
  className,
  ...props
}: React.TdHTMLAttributes<HTMLTableCellElement>): JSX.Element {
  return <td className={cn("p-2 align-middle", className)} {...props} />;
}

