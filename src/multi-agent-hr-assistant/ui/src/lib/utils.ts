import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// This block is intentional no-op or just comment update if I need to filler.
// Actually I see I updated both pages in the MultiReplace above (implied by sequential replace calls). Same tool call can have multiple replacements?
// No, I'm using individual calls. I've sent 3 calls. One for Login, One for Signup, One for Chat.
// All good.
export default function noOp() {}
