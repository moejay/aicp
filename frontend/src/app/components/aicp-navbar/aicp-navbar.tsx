"use client";

import * as React from 'react';
import { useSession, getSession } from "next-auth/react"
import {
  Navbar, 
  NavbarBrand, 
  NavbarContent, 
  NavbarItem, 
  NavbarMenuToggle,
  NavbarMenu,
  NavbarMenuItem,
  Button,
  Avatar,
  DropdownTrigger,
  DropdownMenu,
  DropdownItem,
  Dropdown
} from "@nextui-org/react";

import Link from 'next/link';

const pages = ['Projects', 'Pricing'];

export function AICPNavBar() {
  const { data: session, status } = useSession()
  const email = session?.user?.user?.email
  const username = session?.user?.user?.username
  const photo = session?.user?.user?.photo
  return (

    <Navbar className='flex bg-neutral-600 justify-center'>
    <NavbarBrand className='justify-self-start' >
      <Link href="/">
      <p className="font-bold text-inherit">AUTEUR AI</p>
      </Link>
    </NavbarBrand>
    <NavbarContent className="hidden sm:flex gap-4" justify="center">
      <NavbarItem>
        <Link color="foreground" href="/projects">
         Projects 
        </Link>
      </NavbarItem>
    </NavbarContent>
    <NavbarContent as="div" justify="end">
        <Dropdown placement="bottom-end">
          <DropdownTrigger>
            <Avatar
              isBordered
              as="button"
              className="transition-transform"
              color="secondary"
              name={username}
              size="md"
              src={photo}
            />
          </DropdownTrigger>
          <DropdownMenu aria-label="Profile Actions" variant="flat">
            <DropdownItem key="profile" className="h-14 gap-2">
              <p className="font-semibold">Signed in as</p>
              <p className="font-semibold">{email}</p>
            </DropdownItem>
            <DropdownItem key="divider" className="h-px" />
            <DropdownItem key="profile">
                <Link href="/me">Profile</Link>
            </DropdownItem>
            <DropdownItem key="profile">
                <Link href="/api/auth/signout">Sign Out</Link>
            </DropdownItem>
          </DropdownMenu>
        </Dropdown>
      </NavbarContent>
  </Navbar>

  );
}