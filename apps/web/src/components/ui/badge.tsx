import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset",
  {
    variants: {
      variant: {
        default: "bg-slate-100 text-slate-700 ring-slate-200",
        success: "bg-emerald-100 text-emerald-700 ring-emerald-200",
        warning: "bg-amber-100 text-amber-700 ring-amber-200",
        danger: "bg-red-100 text-red-700 ring-red-200",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps): JSX.Element {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

