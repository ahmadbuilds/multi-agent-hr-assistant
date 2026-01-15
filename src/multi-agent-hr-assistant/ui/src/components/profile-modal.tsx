"use client"

import { useState, useEffect } from "react"
import { createClient } from "@/lib/supabase/client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { User as UserIcon, Camera, Lock } from "lucide-react"
import { toast } from "sonner"

export function ProfileModal() {
  const [open, setOpen] = useState(false)
  const [user, setUser] = useState<any>(null)
  const [fullName, setFullName] = useState("")
  const [username, setUsername] = useState("")
  const [avatarUrl, setAvatarUrl] = useState("")
  const [avatarFile, setAvatarFile] = useState<File | null>(null)
  const [newPassword, setNewPassword] = useState("")
  
  const [loading, setLoading] = useState(false)
  const supabase = createClient()

  useEffect(() => {
    // Fetch initial user
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser()
      if (user) {
         const { data: profile } = await supabase
           .from('users')
           .select('*')
           .eq('id', user.id)
           .single()
         
         if (profile) {
           setUser(profile)
           setFullName(profile.full_name || "")
           setUsername(profile.username || "")
           setAvatarUrl(profile.avatar_url || "")
         } else {
           setUser(user)
           setFullName(user.user_metadata?.full_name || "")
         }
      }
    }
    getUser()
  }, [])

  const handleUpdate = async () => {
    setLoading(true)
    let updatedAvatarUrl = avatarUrl

    if (avatarFile && user) {
        // Enforce "One Image Per User": Wipe the user's folder before uploading
        try {
            console.log("Cleaning up old avatars for:", user.id)
            const { data: files } = await supabase.storage
                .from('avatars')
                .list(user.id) 

            if (files && files.length > 0) {
                const filesToRemove = files.map(f => `${user.id}/${f.name}`)
                console.log("Removing files:", filesToRemove)
                await supabase.storage.from('avatars').remove(filesToRemove)
            }
        } catch (cleanupErr) {
            console.error("Cleanup failed:", cleanupErr)
        }

        const fileExt = avatarFile.name.split('.').pop()
        const fileName = `${user.id}/${Date.now()}.${fileExt}`
        const { error: uploadError } = await supabase.storage
          .from('avatars')
          .upload(fileName, avatarFile)
        
        if (uploadError) {
             console.error("Upload error:", uploadError)
             toast.error("Failed to upload image")
             setLoading(false)
             return
        }

        const { data: urlData } = supabase.storage
            .from('avatars')
            .getPublicUrl(fileName)
        updatedAvatarUrl = urlData.publicUrl
        setAvatarUrl(updatedAvatarUrl)
    }

    const updates = { 
        full_name: fullName,
        username: username,
        avatar_url: updatedAvatarUrl
    }

    // Update user profile
    const { error } = await supabase
      .from('users')
      .update(updates)
      .eq('id', user.id)
    
    if (newPassword) {
        await supabase.auth.updateUser({ password: newPassword })
    }

    setLoading(false)
    if (!error) {
       setOpen(false)
       toast.success("Profile updated successfully")
       window.location.reload() 
    } else {
       console.error("DB Update error:", error)
       toast.error("Failed to update profile database")
    }
  }

  // Basic avatar fallback logic
  const displayAvatar = avatarUrl || user?.user_metadata?.avatar_url 

  return (
    <>
      <Button 
        variant="ghost" 
        className="rounded-full h-10 w-10 p-0 overflow-hidden border border-border shadow-sm hover:ring-2 hover:ring-primary/50 transition-all"
        onClick={() => setOpen(true)}
      >
        {displayAvatar ? (
            <img src={displayAvatar} alt="Avatar" className="h-full w-full object-cover" />
        ) : (
            <div className="h-full w-full bg-primary/20 flex items-center justify-center">
                <UserIcon className="h-5 w-5 text-primary" />
            </div>
        )}
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogHeader>
          <DialogTitle>Edit Profile</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="flex items-center justify-center mb-6">
              <div className="relative group cursor-pointer">
                  <div className="h-24 w-24 rounded-full overflow-hidden border-2 border-dashed border-muted-foreground/50 flex items-center justify-center bg-muted/20">
                    {displayAvatar ? (
                        <img src={displayAvatar} alt="Profile" className="h-full w-full object-cover" />
                    ) : (
                        <UserIcon className="h-8 w-8 text-muted-foreground" />
                    )}
                  </div>
                  <label htmlFor="avatar-upload" className="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity rounded-full cursor-pointer text-white">
                      <Camera className="h-6 w-6" />
                  </label>
                  <input 
                    id="avatar-upload" 
                    type="file" 
                    accept="image/*" 
                    className="hidden" 
                    onChange={(e) => {
                        if (e.target.files?.[0]) {
                            setAvatarFile(e.target.files[0])
                            // Preview
                            setAvatarUrl(URL.createObjectURL(e.target.files[0]))
                        }
                    }} 
                  />
              </div>
          </div>

          <div className="space-y-2">
            <Label>Username</Label>
            <Input 
              value={username} 
              onChange={(e) => setUsername(e.target.value)} 
            />
          </div>

          <div className="space-y-2">
            <Label>Full Name</Label>
            <Input 
              value={fullName} 
              onChange={(e) => setFullName(e.target.value)} 
            />
          </div>

          <div className="space-y-2">
            <Label>New Password (Optional)</Label>
            <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input 
                type="password"
                value={newPassword} 
                onChange={(e) => setNewPassword(e.target.value)} 
                className="pl-9"
                placeholder="Leave blank to keep current"
                />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button variant="ghost" onClick={() => setOpen(false)}>Cancel</Button>
            <Button onClick={handleUpdate} disabled={loading}>Save Changes</Button>
          </div>
        </div>
      </Dialog>
    </>
  )
}
