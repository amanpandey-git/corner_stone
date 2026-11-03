import type { ComponentProps } from "react";
import { cx } from "./cx";

/** A placeholder shaped like the content on its way. */
export function Skeleton({ className, ...rest }: ComponentProps<"div">) {
  return <div aria-hidden className={cx("animate-pulse rounded-sm bg-sunk", className)} {...rest} />;
}
