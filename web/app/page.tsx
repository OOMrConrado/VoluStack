import Image from "next/image";
import {
  Download,
  Code,
  SlidersHorizontal,
  Keyboard,
  AppWindow,
  Moon,
  MonitorSpeaker,
  RefreshCw,
  Github,
} from "lucide-react";

const REPO_URL = "https://github.com/OOMrConrado/VoluStack";
const DOWNLOAD_URL = `${REPO_URL}/releases/latest/download/VoluStack-Setup.exe`;

const features = [
  {
    icon: SlidersHorizontal,
    title: "Per-App Control",
    description: "Individual volume sliders for each application playing audio.",
  },
  {
    icon: Keyboard,
    title: "Global Hotkey",
    description: "Toggle the window instantly with Ctrl+Shift+V.",
  },
  {
    icon: AppWindow,
    title: "System Tray",
    description: "Runs quietly in the background, always one click away.",
  },
  {
    icon: Moon,
    title: "Sleep Mode",
    description: "Near-zero resource usage when the window is hidden.",
  },
  {
    icon: MonitorSpeaker,
    title: "Multi-Device",
    description: "Handles multiple audio output devices seamlessly.",
  },
  {
    icon: RefreshCw,
    title: "Auto-Updater",
    description: "Stay up to date with automatic update notifications.",
  },
];

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col font-[family-name:var(--font-geist-sans)]">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-white/10">
        <div className="flex items-center gap-2">
          <Image src="/icon.ico" alt="VoluStack" width={24} height={24} />
          <span className="text-lg font-semibold tracking-tight">
            VoluStack
          </span>
        </div>
        <a
          href={REPO_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 text-sm text-neutral-400 hover:text-white transition-colors"
        >
          <Github size={16} />
          GitHub
        </a>
      </header>

      {/* Hero */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-24 text-center">
        <Image
          src="/icon.ico"
          alt="VoluStack"
          width={72}
          height={72}
          className="mb-6"
        />
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight max-w-2xl">
          Per-app volume control for Windows
        </h1>
        <p className="mt-4 text-lg text-neutral-400 max-w-lg">
          A lightweight desktop utility that gives you individual volume sliders
          for each running application.
        </p>

        <div className="mt-8 flex gap-3">
          <a
            href={DOWNLOAD_URL}
            className="flex h-11 items-center justify-center gap-2 rounded-lg bg-white px-5 font-medium text-black transition-all hover:bg-neutral-100 hover:scale-[1.02] active:scale-[0.98]"
          >
            <Download size={16} />
            Download
          </a>
          <a
            href={REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="flex h-11 items-center justify-center gap-2 rounded-lg border border-neutral-700 px-5 font-medium transition-all hover:border-neutral-500 hover:bg-white/5 hover:scale-[1.02] active:scale-[0.98]"
          >
            <Github size={16} />
            Source Code
          </a>
        </div>

        <p className="mt-4 text-xs text-neutral-500">
          Windows 10+ &middot; Free &middot; Open Source (MIT)
        </p>
      </main>

      {/* Features */}
      <section className="px-6 py-16 border-t border-white/10">
        <div className="max-w-4xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((f) => (
            <div key={f.title} className="flex gap-3">
              <f.icon size={20} className="text-neutral-400 shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold mb-1">{f.title}</h3>
                <p className="text-sm text-neutral-400">{f.description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-6 border-t border-white/10 text-center text-xs text-neutral-500">
        Made by{" "}
        <a
          href="https://github.com/OOMrConrado"
          target="_blank"
          rel="noopener noreferrer"
          className="hover:text-white transition-colors"
        >
          OOMrConrado
        </a>
      </footer>
    </div>
  );
}
