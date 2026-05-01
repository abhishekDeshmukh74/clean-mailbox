import { api } from "../api/client";

export default function Login() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg">
        <h1 className="mb-2 text-2xl font-semibold">Clean Mailbox</h1>
        <p className="mb-6 text-sm text-slate-600">
          Intelligently label and organize your Gmail. Nothing is ever deleted.
        </p>
        <a
          href={api.loginUrl()}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-700"
        >
          Sign in with Google
        </a>
        <p className="mt-4 text-xs text-slate-500">
          Requires the <code>gmail.modify</code> scope so we can add labels.
        </p>
      </div>
    </div>
  );
}
