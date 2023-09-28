/* Component showing the user profile */
"use client";
import React from 'react';
import { useSession } from 'next-auth/react';
import { Box, Typography } from '@mui/material';

export default function Profile() {
  const { data: session, status } = useSession();
  const loading = status === 'loading';

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!session) {
    return <div>Not signed in</div>;
  }

  return (
    <Box>
      <Typography variant="h4">Profile</Typography>
      <ul>
        {Object.entries(session).map(([key, value]) => (
          <li key={key}>
            <strong>{key}: </strong> {value.toString()}
          </li>
        ))}

      </ul>
    </Box>
  );
}