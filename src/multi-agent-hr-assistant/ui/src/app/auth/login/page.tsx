"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { createClient } from "@/lib/supabase/client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Loader2, Lock, Mail } from "lucide-react"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()
  const supabase = createClient()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) {
      setError(error.message)
      setLoading(false)
    } else {
      router.push("/dashboard")
      router.refresh()
    }
  }

  return (
    <div className="w-full max-w-md p-8 rounded-2xl border border-white/5 bg-card/60 backdrop-blur-xl shadow-2xl relative overflow-hidden">
      {/* Subtle top gloss */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent opacity-50" />
      
      <div className="flex flex-col space-y-2 text-center mb-8">
        <h3 className="font-bold tracking-tight text-3xl text-foreground">Welcome Back</h3>
        <p className="text-sm text-muted-foreground">
          Sign in to access your HR workspace
        </p>
      </div>

      <form onSubmit={handleLogin} className="space-y-5">
          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-lg font-medium animate-fade-in flex items-center justify-center">
              {error}
            </div>
          )}
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
              />
            </div>
          </div>
          <div className="space-y-2 text-left">
            <Label htmlFor="password">Password</Label>
            <div className="relative group">
              <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground transition-colors group-focus-within:text-primary" />
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pl-10 bg-black/20 border-white/10 focus:border-primary/50 focus:bg-black/30 transition-all h-10"
                required
              />
            </div>
          </div>
          <Button type="submit" className="w-full h-10 font-medium shadow-primary/20 shadow-lg hover:shadow-primary/30 transition-all hover:scale-[1.02] active:scale-[0.98]" disabled={loading}>
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Sign In
          </Button>

          <div className="text-center text-sm pt-2">
            <span className="text-muted-foreground">Don&apos;t have an account? </span>
            <Link href="/auth/signup" className="font-medium text-primary hover:text-primary/80 transition-colors underline-offset-4 hover:underline">
              Sign up
            </Link>
          </div>
      </form>
    </div>
  )
}
