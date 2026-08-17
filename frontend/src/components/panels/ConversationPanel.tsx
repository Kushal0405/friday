import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Panel } from '../common/Panel'
import { useFridayStore, type ConversationEntry } from '../../stores/fridayStore'
import './ConversationPanel.css'

export function ConversationPanel() {
  const conversation = useFridayStore((s) => s.conversation)
  const clearConversation = useFridayStore((s) => s.clearConversation)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [conversation.length])

  return (
    <Panel title="CONVERSATION" action={<span onClick={clearConversation}>Clear</span>}>
      {conversation.length === 0 ? (
        <div className="conv-empty">Say "Friday" or type a command to get started.</div>
      ) : (
        <div className="conv-list">
          <AnimatePresence initial={false}>
            {conversation.map((entry, i) => (
              <ConversationBubble
                key={entry.id}
                entry={entry}
                isLatest={i === conversation.length - 1}
              />
            ))}
          </AnimatePresence>
          <div ref={bottomRef} />
        </div>
      )}
    </Panel>
  )
}

function ConversationBubble({ entry, isLatest }: { entry: ConversationEntry; isLatest: boolean }) {
  const typewriter = entry.role === 'friday' && isLatest
  const displayText = useTypewriter(entry.text, typewriter)

  return (
    <motion.div
      className={`conv-bubble conv-${entry.role}`}
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      layout
    >
      {entry.role === 'friday' && <div className="conv-label">FRIDAY</div>}
      <div className="conv-text">{displayText}</div>
    </motion.div>
  )
}

function useTypewriter(text: string, enabled: boolean): string {
  const [shown, setShown] = useState(enabled ? '' : text)

  useEffect(() => {
    if (!enabled) {
      setShown(text)
      return
    }
    setShown('')
    let i = 0
    const step = Math.max(1, Math.round(text.length / 120))
    const id = setInterval(() => {
      i += step
      setShown(text.slice(0, i))
      if (i >= text.length) clearInterval(id)
    }, 12)
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text])

  return shown
}
