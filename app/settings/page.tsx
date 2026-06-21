'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { useRouter } from 'next/navigation';
import { motion } from 'motion/react';
import { Settings, User, Image as ImageIcon, ArrowLeft, Save, Shield, Bell, Volume2 } from 'lucide-react';
import Link from 'next/link';

export default function SettingsPage() {
  const { user, profile, updateUserProfile, linkGoogleAccount } = useAuth();
  const router = useRouter();
  
  const [displayName, setDisplayName] = useState('');
  const [handle, setHandle] = useState('');
  const [photoURL, setPhotoURL] = useState('');
  const [notifications, setNotifications] = useState(true);
  const [soundEnabled, setSoundEnabled] = useState(true);
  
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  useEffect(() => {
    if (!user && !loading) {
      router.push('/auth');
    }
    if (profile) {
      setDisplayName(profile.displayName || '');
      setHandle(profile.handle || '');
      setPhotoURL(profile.photoURL || '');
      setNotifications(profile.settings?.notifications ?? true);
      setSoundEnabled(profile.settings?.soundEnabled ?? true);
      setHasUnsavedChanges(false);
    }
  }, [user, profile, router, loading]);

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges]);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (!hasUnsavedChanges) return;
      const target = e.target as HTMLElement;
      const link = target.closest('a');
      if (link && link.href && link.href !== window.location.href && !link.target) {
        if (!window.confirm('You have unsaved changes. Are you sure you want to leave?')) {
          e.preventDefault();
        }
      }
    };
    document.addEventListener('click', handleClick, { capture: true });
    return () => document.removeEventListener('click', handleClick, { capture: true });
  }, [hasUnsavedChanges]);

  const handleFieldChange = (setter: any) => (e: any) => {
    setter(e.target.value);
    setHasUnsavedChanges(true);
  };

  const handleCheckboxChange = (setter: any) => (e: any) => {
    setter(e.target.checked);
    setHasUnsavedChanges(true);
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ text: '', type: '' });
    
    try {
      await updateUserProfile({
        displayName,
        handle,
        photoURL,
        settings: {
          ...profile?.settings,
          notifications,
          soundEnabled
        }
      });
      setMessage({ text: 'Profile updated successfully!', type: 'success' });
      setHasUnsavedChanges(false);
    } catch (error: any) {
      setMessage({ text: error.message || 'Failed to update profile', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleLinkGoogle = async () => {
    try {
      await linkGoogleAccount();
      setMessage({ text: 'Google account linked successfully!', type: 'success' });
    } catch (error: any) {
      setMessage({ text: error.message || 'Failed to link Google account', type: 'error' });
    }
  };

  if (!profile) return null;

  const isGoogleLinked = user?.providerData.some(p => p.providerId === 'google.com');

  return (
    <main className="min-h-screen dark:text-white text-zinc-900 p-4 sm:p-8">
      <div className="max-w-3xl mx-auto">
        <Link href="/" className="inline-flex items-center gap-2 dark:text-zinc-400 text-zinc-500 hover:text-zinc-900 dark:hover:text-white transition-colors mb-8">
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>

        <div className="flex items-center gap-3 mb-8">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center">
            <Settings className="w-6 h-6 text-emerald-500" />
          </div>
          <h1 className="text-3xl font-bold">Settings</h1>
        </div>

        {message.text && (
          <div className={`mb-6 p-4 rounded-xl text-sm font-medium ${
            message.type === 'success' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'
          }`}>
            {message.text}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="md:col-span-2 space-y-6">
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="dark:bg-zinc-900/40 bg-white border dark:border-zinc-800/50 border-zinc-200 rounded-3xl p-6 shadow-sm"
            >
              <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                <User className="w-5 h-5 text-emerald-500" />
                Public Profile
              </h2>
              
              <form onSubmit={handleSaveProfile} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium dark:text-zinc-400 text-zinc-600 mb-1">Display Name</label>
                  <input
                    type="text"
                    value={displayName}
                    onChange={handleFieldChange(setDisplayName)}
                    className="w-full dark:bg-zinc-950 bg-white border dark:border-zinc-800 border-zinc-300 rounded-xl py-2.5 px-4 dark:text-white text-zinc-900 focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium dark:text-zinc-400 text-zinc-600 mb-1">Username / Handle</label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500">@</span>
                    <input
                      type="text"
                      value={handle}
                      onChange={handleFieldChange(setHandle)}
                      className="w-full dark:bg-zinc-950 bg-white border dark:border-zinc-800 border-zinc-300 rounded-xl py-2.5 pl-8 pr-4 dark:text-white text-zinc-900 focus:outline-none focus:border-emerald-500 transition-colors"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium dark:text-zinc-400 text-zinc-600 mb-1">Profile Picture URL</label>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <ImageIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                      <input
                        type="url"
                        value={photoURL}
                        onChange={handleFieldChange(setPhotoURL)}
                        placeholder="https://example.com/image.png"
                        className="w-full dark:bg-zinc-950 bg-white border dark:border-zinc-800 border-zinc-300 rounded-xl py-2.5 pl-10 pr-4 dark:text-white text-zinc-900 focus:outline-none focus:border-emerald-500 transition-colors"
                      />
                    </div>
                    <label className="cursor-pointer flex items-center justify-center px-4 py-2.5 dark:bg-zinc-800 bg-zinc-200 dark:hover:bg-zinc-700 hover:bg-zinc-300 dark:text-white text-zinc-900 rounded-xl font-medium transition-colors border dark:border-zinc-700 border-zinc-300">
                      Upload
                      <input 
                        type="file" 
                        accept="image/*" 
                        className="hidden" 
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) {
                            const reader = new FileReader();
                            reader.onload = (event) => {
                              const img = new Image();
                              img.onload = () => {
                                const canvas = document.createElement('canvas');
                                const MAX_WIDTH = 128;
                                const MAX_HEIGHT = 128;
                                let width = img.width;
                                let height = img.height;

                                if (width > height) {
                                  if (width > MAX_WIDTH) {
                                    height *= MAX_WIDTH / width;
                                    width = MAX_WIDTH;
                                  }
                                } else {
                                  if (height > MAX_HEIGHT) {
                                    width *= MAX_HEIGHT / height;
                                    height = MAX_HEIGHT;
                                  }
                                }
                                canvas.width = width;
                                canvas.height = height;
                                const ctx = canvas.getContext('2d');
                                ctx?.drawImage(img, 0, 0, width, height);
                                const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
                                setPhotoURL(dataUrl);
                                setHasUnsavedChanges(true);
                              };
                              img.src = event.target?.result as string;
                            };
                            reader.readAsDataURL(file);
                          }
                        }}
                      />
                    </label>
                  </div>
                </div>

                <div className="pt-4">
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex items-center gap-2 px-6 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white font-bold rounded-xl transition-colors disabled:opacity-50"
                  >
                    <Save className="w-4 h-4" />
                    Save Profile
                  </button>
                </div>
              </form>
            </motion.section>

            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="dark:bg-zinc-900/40 bg-white border dark:border-zinc-800/50 border-zinc-200 rounded-3xl p-6 shadow-sm"
            >
              <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                <Shield className="w-5 h-5 text-purple-500" />
                Account Security
              </h2>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 dark:bg-zinc-950 bg-zinc-50 rounded-xl border dark:border-zinc-800 border-zinc-200">
                  <div>
                    <div className="font-bold">Email Address</div>
                    <div className="text-sm dark:text-zinc-400 text-zinc-500">{user?.email}</div>
                  </div>
                  <div className="px-3 py-1 dark:bg-zinc-800 bg-zinc-200 dark:text-zinc-300 text-zinc-700 text-xs font-bold rounded-md">
                    Verified
                  </div>
                </div>

                {!isGoogleLinked && (
                  <div className="flex items-center justify-between p-4 dark:bg-zinc-950 bg-zinc-50 rounded-xl border dark:border-zinc-800 border-zinc-200">
                    <div>
                      <div className="font-bold">Google Account</div>
                      <div className="text-sm dark:text-zinc-400 text-zinc-500">Link your Google account for easier login</div>
                    </div>
                    <button
                      onClick={handleLinkGoogle}
                      className="px-4 py-2 dark:bg-white bg-zinc-900 dark:hover:bg-zinc-200 hover:bg-zinc-800 dark:text-black text-white text-sm font-bold rounded-xl transition-colors"
                    >
                      Link Google
                    </button>
                  </div>
                )}
              </div>
            </motion.section>
          </div>

          <div className="space-y-6">
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="dark:bg-zinc-900/40 bg-white border dark:border-zinc-800/50 border-zinc-200 rounded-3xl p-6 shadow-sm"
            >
              <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                <Bell className="w-5 h-5 text-blue-500" />
                Preferences
              </h2>
              
              <div className="space-y-4">
                <label className="flex items-center justify-between cursor-pointer">
                  <div>
                    <div className="font-bold text-sm">Notifications</div>
                    <div className="text-xs dark:text-zinc-400 text-zinc-500">Match updates and news</div>
                  </div>
                  <div className="relative">
                    <input
                      type="checkbox"
                      className="sr-only"
                      checked={notifications}
                      onChange={handleCheckboxChange(setNotifications)}
                    />
                    <div className={`block w-10 h-6 rounded-full transition-colors ${notifications ? 'bg-emerald-500' : 'dark:bg-zinc-700 bg-zinc-300'}`}></div>
                    <div className={`absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${notifications ? 'translate-x-4' : ''}`}></div>
                  </div>
                </label>

                <label className="flex items-center justify-between cursor-pointer">
                  <div>
                    <div className="font-bold text-sm flex items-center gap-1.5">
                      <Volume2 className="w-4 h-4" /> Sound Effects
                    </div>
                    <div className="text-xs dark:text-zinc-400 text-zinc-500">In-game audio</div>
                  </div>
                  <div className="relative">
                    <input
                      type="checkbox"
                      className="sr-only"
                      checked={soundEnabled}
                      onChange={handleCheckboxChange(setSoundEnabled)}
                    />
                    <div className={`block w-10 h-6 rounded-full transition-colors ${soundEnabled ? 'bg-emerald-500' : 'dark:bg-zinc-700 bg-zinc-300'}`}></div>
                    <div className={`absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${soundEnabled ? 'translate-x-4' : ''}`}></div>
                  </div>
                </label>
              </div>
            </motion.section>
          </div>
        </div>
      </div>
    </main>
  );
}
