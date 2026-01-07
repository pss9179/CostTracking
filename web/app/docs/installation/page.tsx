"use client";

import Link from "next/link";
import { DocPage, CodeBlock, Callout } from "@/components/docs/DocPage";

const toc = [
  { id: "requirements", title: "Requirements" },
  { id: "pip-install", title: "Install with pip" },
  { id: "poetry-install", title: "Install with Poetry" },
  { id: "verify", title: "Verify installation" },
];

export default function InstallationPage() {
  return (
    <DocPage
      title="Installation"
      description="Install the LLMObserve Python SDK in your project."
      category="Getting started"
      toc={toc}
    >
      <h2 id="requirements">Requirements</h2>

      <ul>
        <li><strong>Python 3.8+</strong></li>
        <li>One of: httpx, requests, or aiohttp (for HTTP interception)</li>
      </ul>

      <Callout type="info">
        Most LLM SDKs (OpenAI, Anthropic, etc.) use httpx internally, so you likely 
        already have a compatible HTTP client.
      </Callout>

      <h2 id="pip-install">Install with pip</h2>

      <CodeBlock code="pip install llmobserve" language="bash" filename="Terminal" />

      <p>To install a specific version:</p>

      <CodeBlock code="pip install llmobserve==1.0.0" language="bash" filename="Terminal" />

      <h2 id="poetry-install">Install with Poetry</h2>

      <CodeBlock code="poetry add llmobserve" language="bash" filename="Terminal" />

      <h2 id="verify">Verify installation</h2>

      <p>Check that llmobserve is installed correctly:</p>

      <CodeBlock
        code={`python -c "import llmobserve; print(llmobserve.__version__)"`}
        language="bash"
        filename="Terminal"
      />

      <p>You should see the version number printed.</p>

      <hr />

      <h3>Next steps</h3>

      <ul>
        <li><Link href="/docs/quickstart">Quickstart guide</Link></li>
        <li><Link href="/docs/sdk">SDK Reference</Link></li>
      </ul>
    </DocPage>
  );
}

