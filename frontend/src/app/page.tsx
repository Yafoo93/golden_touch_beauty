import Image from "next/image";

type HealthResponse = {
  application: string;
  status: string;
  database: string;
};

async function getBackendHealth(): Promise<HealthResponse | null> {
  const baseUrl = process.env.BACKEND_INTERNAL_URL;

  if (!baseUrl) {
    return null;
  }

  try {
    const response = await fetch(`${baseUrl}/health/`, {
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    return response.json();
  } catch {
    return null;
  }
}

export default async function Home() {
  const backend = await getBackendHealth();

  return (
    <main className="min-h-screen bg-black px-6 py-16 text-white">
      <div className="mx-auto max-w-5xl text-center">
        <Image
          src="/images/logo.png"
          alt="Golden Touch Beauty Centre"
          width={180}
          height={180}
          className="mx-auto"
          priority
        />

        <h1 className="mt-8 text-4xl font-semibold text-amber-400">
          Golden Touch Beauty Centre
        </h1>

        <p className="mt-3 text-lg text-neutral-300">
          Where Beauty Meets Excellence
        </p>

        <div className="mx-auto mt-10 max-w-md rounded-xl border border-amber-500/30 bg-neutral-900 p-6">
          <p className="text-sm uppercase tracking-wider text-neutral-400">
            System connection
          </p>

          <p className="mt-3 text-xl font-medium">
            Backend:{" "}
            <span
              className={
                backend?.status === "ok"
                  ? "text-green-400"
                  : "text-red-400"
              }
            >
              {backend?.status === "ok"
                ? "Connected"
                : "Unavailable"}
            </span>
          </p>

          <p className="mt-2 text-neutral-400">
            Database: {backend?.database ?? "Unknown"}
          </p>
        </div>
      </div>
    </main>
  );
}
