import { useState, type FormEvent } from 'react'
import { fridaySocket } from '../../services/websocket'
import './TextInput.css'

export function TextInput() {
  const [value, setValue] = useState('')

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const text = value.trim()
    if (!text) return
    fridaySocket.send({ type: 'user_text', text })
    setValue('')
  }

  return (
    <form className="text-input" onSubmit={handleSubmit}>
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Type a command…"
        autoFocus
      />
    </form>
  )
}
