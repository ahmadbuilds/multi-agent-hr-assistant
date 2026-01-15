"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { createClient } from "@/lib/supabase/client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Loader2, Mail, Lock, User, Upload } from "lucide-react"

export default function SignupPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [username, setUsername] = useState("")
  const [needsConfirmation, setNeedsConfirmation] = useState(false)
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const router = useRouter()
  const supabase = createClient()

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    if (password !== confirmPassword) {
      setError("Passwords do not match")
      setLoading(false)
      return
    }

    try {
      // 1. Sign up user
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            username,
            full_name: username,
          },
          emailRedirectTo: `${window.location.origin}/auth/callback`
        },
      })

      if (authError) throw authError
      
      // If session is null, email confirmation is required
      if (authData.user && !authData.session) {
         setNeedsConfirmation(true)
         setLoading(false)
         return
      }

      // If we *do* have a session (auto-confirm enabled), proceeds as normal
      if (authData.user) {
        router.push("/dashboard")
        router.refresh()
      }
      
    } catch (err: any) {
      setError(err.message || "Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  if (needsConfirmation) {
    return (
       <div className="rounded-xl border bg-card text-card-foreground shadow-xl p-8 text-center space-y-4">
           <div className="flex justify-center">
              <div className="h-12 w-12 bg-primary/20 rounded-full flex items-center justify-center">
                  <Mail className="h-6 w-6 text-primary" />
              </div>
           </div>
           <h3 className="font-semibold text-2xl">Check your email</h3>
           <p className="text-muted-foreground">
             We sent a confirmation link to <strong>{email}</strong>. <br/>
             Click the link to verify your account and sign in.
           </p>
           <Button variant="outline" onClick={() => router.push('/auth/login')} className="w-full">
             Back to Login
           </Button>
       </div>
    )
  }

  return (
    <div className="w-full max-w-md p-8 rounded-2xl border border-white/5 bg-card/60 backdrop-blur-xl shadow-2xl relative overflow-hidden">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent opacity-50" />
      
      <div className="flex flex-col space-y-2 text-center mb-8">
        <h3 className="font-bold tracking-tight text-3xl text-foreground">Create Account</h3>
        <p className="text-sm text-muted-foreground">
          Join to get started
        </p>
      </div>

      <form onSubmit={handleSignup} className="space-y-5">
          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-lg font-medium animate-fade-in flex items-center justify-center">
              {error}
            </div>
          )}
          
          <div className="space-y-2 text-left">
            <Label htmlFor="username">Username</Label>
            <div className="relative group">
              <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground transition-colors group-focus-within:text-primary" />
              <Input
                id="username"
                placeholder="johndoe"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="pl-10 bg-black/20 border-white/10 focus:border-primary/50 focus:bg-black/30 transition-all h-10"
                required
                minLength={3}
                autoComplete="off"
              />
            </div>
          </div>

          <div className="space-y-2 text-left">
            <Label htmlFor="email">Email</Label>
            <div className="relative group">
              <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground transition-colors group-focus-within:text-primary" />
              <Input
                id="email"
                placeholder="m@example.com"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="pl-10 bg-black/20 border-white/10 focus:border-primary/50 focus:bg-black/30 transition-all h-10"
                required
                autoComplete="new-password"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 text-left">
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-black/20 border-white/10 focus:border-primary/50 focus:bg-black/30 transition-all h-10"
                required
                minLength={6}
                autoComplete="new-password"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm">Confirm</Label>
              <Input
                id="confirm"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="bg-black/20 border-white/10 focus:border-primary/50 focus:bg-black/30 transition-all h-10"
                required
                minLength={6}
                autoComplete="new-password"
              />
            </div>
          </div>

          <Button type="submit" className="w-full h-10 font-medium shadow-primary/20 shadow-lg hover:shadow-primary/30 transition-all hover:scale-[1.02] active:scale-[0.98]" disabled={loading}>
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Sign Up
          </Button>

          <div className="text-center text-sm pt-2">
            <span className="text-muted-foreground">Already have an account? </span>
            <Link href="/auth/login" className="font-medium text-primary hover:text-primary/80 transition-colors underline-offset-4 hover:underline">
              Sign in
            </Link>
          </div>
        </form>
    </div>
  )
}
