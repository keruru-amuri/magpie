import NextAuth from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import { JWT } from 'next-auth/jwt';

// Define custom session type
interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  image?: string;
  firstName?: string;
  lastName?: string;
}

// Define custom session type
interface Session {
  user: User;
  expires: string;
}

// Define custom token type
interface Token extends JWT {
  user?: User;
  accessToken?: string;
}

// Configure NextAuth with a simplified setup for testing
export const {
  handlers,
  auth,
  signIn,
  signOut
} = NextAuth({
  secret: process.env.NEXTAUTH_SECRET || 'magpie_development_secret_key',
  pages: {
    signIn: '/login',
    signOut: '/logout',
    error: '/auth/error',
    newUser: '/register'
  },
  callbacks: {
    async jwt({ token, user }) {
      // Initial sign in
      if (user) {
        token.user = user as User;
      }
      return token;
    },
    async session({ session, token }) {
      // Send properties to the client
      if (token.user) {
        session.user = token.user as User;
      } else {
        // For testing, provide a mock user if none exists
        session.user = {
          id: '1',
          name: 'Test User',
          email: 'test@example.com',
          role: 'user',
          firstName: 'Test',
          lastName: 'User'
        };
      }
      return session;
    },
    async authorized({ request }) {
      // For testing purposes, allow access to all pages
      return true;
    },
  },
  providers: [
    Credentials({
      name: 'Credentials',
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize() {
        // For testing, always return a mock user
        return {
          id: '1',
          name: 'Test User',
          email: 'test@example.com',
          role: 'user',
          firstName: 'Test',
          lastName: 'User'
        };
      }
    })
  ],
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60, // 30 days
  }
});
