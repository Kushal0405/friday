import { useEffect, useRef } from 'react'
import { Panel } from '../common/Panel'
import { useFridayStore } from '../../stores/fridayStore'
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
          {conversation.map((entry) => (
            <div key={entry.id} className={`conv-bubble conv-${entry.role}`}>
              {entry.role === 'friday' && <div className="conv-label">FRIDAY</div>}
              <div className="conv-text">{entry.text}</div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      )}
    </Panel>
  )
}
