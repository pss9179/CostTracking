"use client";

import Link from "next/link";
import { DocPage, Callout } from "@/components/docs/DocPage";

const toc = [
  { id: "alert-types", title: "Alert types" },
  { id: "configuring-alerts", title: "Configuring alerts" },
  { id: "notification-channels", title: "Notification channels" },
];

export default function AlertsPage() {
  return (
    <DocPage
      title="Alerts & notifications"
      description="Get notified when spending approaches or exceeds your limits."
      category="Spending controls"
      toc={toc}
    >
      <h2 id="alert-types">Alert types</h2>

      <p>LLMObserve can send alerts for:</p>

      <h3>Spending cap alerts</h3>
      <ul>
        <li><strong>80% threshold</strong> — Early warning as you approach your cap</li>
        <li><strong>95% threshold</strong> — Urgent warning before hitting the cap</li>
        <li><strong>100% threshold</strong> — Cap has been reached</li>
      </ul>

      <h3>Anomaly alerts</h3>
      <ul>
        <li><strong>Spending spike</strong> — Unusual increase in spending rate</li>
        <li><strong>High-cost customer</strong> — Customer exceeding normal usage</li>
      </ul>

      <h2 id="configuring-alerts">Configuring alerts</h2>

      <p>
        Configure alerts in <Link href="/settings">Settings → Notifications</Link>:
      </p>

      <ol>
        <li>Navigate to Settings</li>
        <li>Click "Notifications"</li>
        <li>Enable the alerts you want to receive</li>
        <li>Set your preferred thresholds</li>
      </ol>

      <Callout type="info">
        Alert thresholds are configured per spending cap. When you create or edit a cap, 
        you can choose which thresholds trigger notifications.
      </Callout>

      <h2 id="notification-channels">Notification channels</h2>

      <h3>Email</h3>
      <p>
        Alerts are sent to your account email by default. Add additional recipients in 
        Settings → Notifications.
      </p>

      <h3>Coming soon</h3>
      <ul>
        <li>Slack integration</li>
        <li>Webhook notifications</li>
        <li>PagerDuty integration</li>
      </ul>

      <hr />

      <h3>See also</h3>

      <ul>
        <li><Link href="/docs/spending-caps">Spending caps</Link></li>
        <li><Link href="/settings">Settings page</Link></li>
      </ul>
    </DocPage>
  );
}

