import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/auth';

export async function POST(request: NextRequest) {
  try {
    // Get the session
    const session = await auth();
    
    // Check if user is authenticated
    if (!session || !session.user) {
      return NextResponse.json(
        { message: 'Unauthorized' },
        { status: 401 }
      );
    }
    
    // Get request body
    const body = await request.json();
    
    // Validate required fields
    if (!body.currentPassword || !body.newPassword) {
      return NextResponse.json(
        { message: 'Current password and new password are required' },
        { status: 400 }
      );
    }
    
    // Call the backend API to change password
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/user/change-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${(session as any).accessToken}`,
      },
      body: JSON.stringify({
        current_password: body.currentPassword,
        new_password: body.newPassword,
      }),
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      return NextResponse.json(
        { message: data.detail || 'Failed to change password' },
        { status: response.status }
      );
    }
    
    return NextResponse.json({ 
      message: 'Password changed successfully' 
    });
  } catch (error) {
    console.error('Change password error:', error);
    return NextResponse.json(
      { message: 'An unexpected error occurred' },
      { status: 500 }
    );
  }
}
