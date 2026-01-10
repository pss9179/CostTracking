import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-100 via-white to-slate-100">
      <SignIn
        appearance={{
          elements: {
            rootBox: "mx-auto w-full max-w-md",
            card: "bg-white border border-gray-200 shadow-2xl rounded-2xl p-8 w-full",
            headerTitle: "text-gray-900 text-3xl font-bold",
            headerSubtitle: "text-gray-600 text-base mt-2",
            socialButtonsBlockButton: "bg-white hover:bg-gray-50 border border-gray-200 text-gray-900 transition-all duration-200 shadow-sm py-3 text-base",
            socialButtonsBlockButtonText: "text-gray-900 font-medium text-base",
            formButtonPrimary: "bg-gray-900 hover:bg-gray-800 text-white font-semibold shadow-sm transition-all duration-200 py-3 text-base",
            formFieldInput: "bg-white border-gray-300 text-gray-900 placeholder:text-gray-400 focus:border-gray-900 focus:ring-gray-900 py-3 text-base",
            formFieldLabel: "text-gray-700 text-sm font-medium",
            footerActionLink: "text-gray-900 hover:text-gray-700 font-medium",
            identityPreviewText: "text-gray-900",
            identityPreviewEditButton: "text-gray-700 hover:text-gray-900",
            dividerLine: "bg-gray-200",
            dividerText: "text-gray-500 text-sm",
            formResendCodeLink: "text-gray-900 hover:text-gray-700",
            alertText: "text-gray-900",
            footer: "hidden",
          },
          layout: {
            socialButtonsPlacement: "top",
          },
        }}
      />
    </div>
  );
}
