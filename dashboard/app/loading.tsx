import LoadingSpinner from "@/components/LoadingSpinner";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

export default function Loading() {
  return (
    <>
      <Header />
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <LoadingSpinner />
      </main>
      <Footer />
    </>
  );
}
