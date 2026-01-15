"use client"

import { ProfileModal } from "@/components/profile-modal"
import { useEffect, useState } from "react"

export function Header() {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <div className="absolute top-4 right-4 z-50 flex items-center gap-2">
      <ProfileModal />
    </div>
  )
}
