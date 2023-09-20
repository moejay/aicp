/**
 * Login Page Component
 */
"use client";
import React,{ useState } from 'react';


export default function LoginPage() {
    const [error, setError] = useState<string | null>(null);
    
    const handleSubmit = async (email: string, password: string) => {
        setError(null);
    
        try {
        } catch (err) {
        }
    };
    
    return (
        <div className="flex flex-col items-center justify-center min-h-screen px-4 py-12 bg-gray-50 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center w-full max-w-md space-y-8">
            <div>
            <h2 className="text-3xl font-extrabold text-gray-900">Sign in to your account</h2>
            </div>
    
        </div>
        </div>
    );
}