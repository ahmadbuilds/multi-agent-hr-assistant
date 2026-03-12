"use client"

import { ProfileModal } from "@/components/profile-modal"

export function Header() {
  return (
    <div className="absolute top-4 right-4 z-50 flex items-center gap-2">
      <ProfileModal />
    </div>
  )
}
