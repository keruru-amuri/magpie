import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Validate email
    if (!body.email) {
      return NextResponse.json(
        { message: 'Email is required' },
        { status: 400 }
      );
    }
    
    // Call the backend API to request password reset
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/forgot-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email: body.email }),
    });
    
    // For security reasons, always return success even if the email doesn't exist
    return NextResponse.json({ 
      message: 'If an account with that email exists, a password reset link has been sent' 
    });
  } catch (error) {
    console.error('Password reset request error:', error);
    
    // For security reasons, don't expose the error
    return NextResponse.json({ 
      message: 'If an account with that email exists, a password reset link has been sent' 
    });
  }
}
