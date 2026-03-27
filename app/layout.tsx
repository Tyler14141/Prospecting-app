import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Harris Prospecting Agent',
  description: 'ICP-driven municipal sales prospecting for Harris Computer',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans">{children}</body>
    </html>
  )
}
