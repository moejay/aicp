import { signOut } from "next-auth/react";
import React from "react";

export default function SignOutPage() {
    signOut({
        redirect: true,
        callbackUrl: "/",
    })
    return (
        <div>
            <h1>Sign Out</h1>
        </div>
    )
}

    