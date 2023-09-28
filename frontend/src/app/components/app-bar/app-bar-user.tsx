/* Component to display current logged in user, or sign in button if not logged in */
"use client";
import React from 'react';
import Box from '@mui/material/Box';
import {signIn, signOut, useSession } from 'next-auth/react';
import Tooltip from '@mui/material/Tooltip';
import { Button } from '@mui/material';

const settings = ['Profile', 'Account', 'Logout'];

export default function AppBarUser() {
    const {data: session, status} = useSession();
    const loading = status === 'loading';

    return ( 
    <Box sx={{ flexGrow: 0 }}>
        {session && (
            <Button onClick={() => signOut()} variant="contained">Sign out</Button>
            )}
        {!session && (
            <Tooltip title="Sign in">
                <Button onClick={() => signIn()} variant="contained">Sign in</Button>
            </Tooltip>
        )}
        </Box>
    )
}