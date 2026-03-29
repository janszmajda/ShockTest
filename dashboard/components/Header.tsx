import Link from "next/link";
import Image from "next/image";

export default function Header() {
  return (
    <nav className="sticky top-0 z-50 bg-surface-base" style={{ borderBottom: "2px solid var(--st-accent)" }}>
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        <Link href="/" className="block">
          <Image
            src="/Frame 9.svg"
            alt="ShockTEST"
            width={120}
            height={80}
            className="h-11 w-auto"
            priority
          />
        </Link>
      </div>
    </nav>
  );
}
