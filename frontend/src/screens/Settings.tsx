import { ArrowLeft, LogOut, Key, User } from "lucide-react";
import { Button } from "../components/Button";
import { getAuth, signOut } from "firebase/auth";

interface SettingsPageProps {
  onBack: () => void;
}

export function SettingsPage({ onBack }: SettingsPageProps) {
  const auth = getAuth();
  const user = auth.currentUser;

  const handleLogout = async () => {
    try {
      await signOut(auth);
      window.location.href = "/"; // or return to login screen based on routing
    } catch (error) {
      console.error("Logout error:", error);
    }
  };

  // Generate initial from name or fallback
  const getInitial = () => {
    if (user?.displayName) return user.displayName.charAt(0).toUpperCase();
    return user?.email?.charAt(0).toUpperCase() || "U";
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div
        className="px-6 py-6 text-white relative"
        style={{ backgroundColor: "#4A8B6F" }}
      >
        <div className="max-w-md mx-auto">
          <div className="flex items-center gap-4">
            <button 
              onClick={onBack}
              className="p-2 -ml-2 hover:bg-white/10 rounded-full transition-colors"
            >
              <ArrowLeft className="w-6 h-6" />
            </button>
            <h1 className="text-xl font-semibold text-white">Settings</h1>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-md mx-auto px-6 py-6 space-y-6 flex-1">
        
        {/* Profile Section */}
        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <div className="flex items-center gap-4">
            <div
              className="w-16 h-16 rounded-full flex items-center justify-center text-white text-2xl font-medium"
              style={{ backgroundColor: "#90CDB5" }}
            >
              {getInitial()}
            </div>
            <div>
              <h3 className="text-lg text-gray-900 font-medium">
                {user?.displayName || "User"}
              </h3>
              <p className="text-sm text-gray-500">{user?.email || "no-email"}</p>
            </div>
          </div>
        </div>

        {/* Account Actions */}
        <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
          <button className="w-full px-6 py-4 flex items-center gap-3 hover:bg-gray-50 transition-colors">
            <Key className="w-5 h-5 text-gray-400" />
            <span className="text-sm text-gray-900">Reset Password</span>
          </button>
        </div>

        {/* Logout */}
        <Button
          onClick={handleLogout}
          variant="outline"
          className="w-full text-red-600 border-red-200 hover:bg-red-50 hover:text-red-700"
        >
          <LogOut className="w-4 h-4 mr-2" />
          Log Out
        </Button>
      </div>

      {/* Footer */}
      <p className="text-center text-xs text-gray-400 py-4">
        Nala Health Coaching © {new Date().getFullYear()}
      </p>
    </div>
  );
}
