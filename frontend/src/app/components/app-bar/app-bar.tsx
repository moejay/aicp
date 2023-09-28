import * as React from 'react';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Container from '@mui/material/Container';
import VideoLibraryIcon from '@mui/icons-material/VideoLibraryOutlined';
import Link from 'next/link';
import AppBarUser from './app-bar-user';

const pages = ['Projects', 'Pricing'];

export function ResponsiveAppBar() {
  
  return (
    <AppBar position="static">
      <Container maxWidth="xl">
        <Toolbar disableGutters>
          <VideoLibraryIcon sx={{ display: { xs: 'none', md: 'flex' }, mr: 1 }} />
          <Typography
            variant="h6"
            noWrap
            component="a"
            href="/"
            sx={{
              mr: 2,
              display: { xs: 'none', md: 'flex' },
              fontFamily: 'monospace',
              fontWeight: 700,
              letterSpacing: '.3rem',
              color: 'inherit',
              textDecoration: 'none',
            }}
          >
           AUTEUR 
          </Typography>

          <Box sx={{ flexGrow: 1, display: { md: 'flex' } }}>
              {pages.map((page) => (
                <Link key={page} href={page.toLowerCase()}>{page}</Link>
              ))}
          </Box>
           <AppBarUser />
        </Toolbar>
      </Container>
    </AppBar>
  );
}