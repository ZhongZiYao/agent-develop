/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      // 代理 API 请求到后端（解决跨域）
      {
        source: "/api/proxy/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000"}/api/v1/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;