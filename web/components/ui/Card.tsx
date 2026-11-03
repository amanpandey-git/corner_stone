import type { ComponentProps } from "react";
import { cx } from "./cx";

export function Card({ className, ...rest }: ComponentProps<"div">) {
  return <div className={cx("rounded-lg border bg-raised", className)} {...rest} />;
}
