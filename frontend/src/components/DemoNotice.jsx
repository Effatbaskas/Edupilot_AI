import { FlaskConical, Info } from 'lucide-react'

export function DemoPill() {
  return <span className="demo-pill"><FlaskConical size={13} /> Demo data</span>
}

export default function DemoNotice({ children = 'This preview uses sample data in your browser. It is not saved to the EduPilot server.' }) {
  return <div className="demo-notice"><Info size={17} /><span><strong>Demo preview:</strong> {children}</span></div>
}
