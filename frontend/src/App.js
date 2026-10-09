import { useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider } from "@/context/AuthContext";
import { SlipProvider } from "@/context/SlipContext";
import { AgeGate } from "@/components/AgeGate";
import { Layout } from "@/components/Layout";
import MeetingsPage from "@/pages/MeetingsPage";
import MeetingPage from "@/pages/MeetingPage";
import AcesPage from "@/pages/AcesPage";
import BestBetsPage from "@/pages/BestBetsPage";
import PlungesPage from "@/pages/PlungesPage";
import ResultsPage from "@/pages/ResultsPage";
import ReportsPage from "@/pages/ReportsPage";
import PricingPage from "@/pages/PricingPage";
import PaymentSuccessPage from "@/pages/PaymentSuccessPage";
import AuthPage from "@/pages/AuthPage";
import AdminPage from "@/pages/AdminPage";
import GuidePage from "@/pages/GuidePage";
import ResetPasswordPage from "@/pages/ResetPasswordPage";
import ExoticsPage from "@/pages/ExoticsPage";
import AccountPage from "@/pages/AccountPage";

function App() {
  const [ageOk, setAgeOk] = useState(() => localStorage.getItem("pr_age18") === "1");

  if (!ageOk) {
    return <AgeGate onConfirm={() => { localStorage.setItem("pr_age18", "1"); setAgeOk(true); }} />;
  }

  return (
    <AuthProvider>
      <SlipProvider>
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<MeetingsPage />} />
              <Route path="/meeting/:id" element={<MeetingPage />} />
              <Route path="/aces" element={<AcesPage />} />
              <Route path="/best-bets" element={<BestBetsPage />} />
              <Route path="/plunges" element={<PlungesPage />} />
              <Route path="/market" element={<PlungesPage />} />
              <Route path="/exotics" element={<ExoticsPage />} />
              <Route path="/account" element={<AccountPage />} />
              <Route path="/results" element={<ResultsPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/pricing" element={<PricingPage />} />
              <Route path="/payment/success" element={<PaymentSuccessPage />} />
              <Route path="/payment/cancel" element={<Navigate to="/pricing" />} />
              <Route path="/pay-success" element={<PaymentSuccessPage />} />
              <Route path="/pay-cancel" element={<Navigate to="/pricing" />} />
              <Route path="/auth" element={<AuthPage />} />
              <Route path="/admin" element={<AdminPage />} />
              <Route path="/guide" element={<GuidePage />} />
              <Route path="/reset-password" element={<ResetPasswordPage />} />
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </Layout>
        </BrowserRouter>
        <Toaster theme="dark" position="top-center" />
      </SlipProvider>
    </AuthProvider>
  );
}

export default App;
