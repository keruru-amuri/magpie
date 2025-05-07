import { NextResponse } from 'next/server';
import { auth } from './auth';

// For development, we'll bypass authentication completely
export default auth((req) => {
  // Always continue with the request - no authentication checks
  return NextResponse.next();
});

// Specify which routes this middleware should run on
export const config = {
  matcher: [
    // Match all routes except static files, images, and other assets
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
