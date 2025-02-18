/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8080',
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: '${process.env.API_BASE_URL || "http://localhost:8080"}/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig 