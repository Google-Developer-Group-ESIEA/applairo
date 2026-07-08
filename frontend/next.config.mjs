/** @type {import('next').NextConfig} */
const nextConfig = {
  // Build « standalone » : produit un serveur Node autonome (.next/standalone)
  // avec ses seules dépendances runtime, image Docker minimale.
  output: "standalone",
};

export default nextConfig;
