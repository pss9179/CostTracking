import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 via-white to-gray-50">
      <SignUp
        appearance={{
          elements: {
            rootBox: "mx-auto",
            card: "bg-white border border-gray-200 shadow-lg rounded-2xl",
            headerTitle: "text-gray-900 text-2xl font-bold",
            headerSubtitle: "text-gray-600",
            socialButtonsBlockButton: "bg-white hover:bg-gray-50 border border-gray-200 text-gray-900 transition-all duration-200 shadow-sm",
            socialButtonsBlockButtonText: "text-gray-900 font-medium",
            formButtonPrimary: "bg-indigo-600 hover:bg-indigo-700 text-white font-semibold shadow-sm transition-all duration-200",
            formFieldInput: "bg-white border-gray-200 text-gray-900 placeholder:text-gray-400 focus:border-indigo-500 focus:ring-indigo-500",
            formFieldLabel: "text-gray-700",
            footerActionLink: "text-indigo-600 hover:text-indigo-700",
            identityPreviewText: "text-gray-900",
            identityPreviewEditButton: "text-indigo-600 hover:text-indigo-700",
            dividerLine: "bg-gray-200",
            dividerText: "text-gray-500",
            formResendCodeLink: "text-indigo-600 hover:text-indigo-700",
            alertText: "text-gray-900",
          },
          layout: {
            socialButtonsPlacement: "top",
          },
        }}
      />
    </div>
  );
}
