import {authenticate, refresh} from "@/api"
import NextAuth from "next-auth"
import { AuthOptions } from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials"
import { Session } from "@/app/types/next-auth"

const jwt = async ({ token, user , account}: { token: JWT; user?: User ; account?: any}) => {
  console.log("jwt function called")
  console.log(token)
  console.log(user)
  console.log(account)
  // first call of jwt function just user object is provided
  if (user && account) {
    token["user"] = user;
    token["access_token"] = user.access_token
    token["refresh_token"] = user.refresh_token
    token["ref"] = token["exp"]
    return token;
  }
  if (getCurrentEpochTime() > token["ref"]) {
    // refresh token
    console.log("refreshing token")
    const res = await refresh(token["refresh_token"])
    token["access_token"] = res.access_token
  }
  return token

  };

const session = ({ token }: { session: Session; token: JWT }): Promise<Session> => {
  console.log("session function called")
  console.log(token)
  return token
  };

export const authOptions: AuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" }
      },
      async authorize (credentials, req) {
        if (typeof credentials !== "undefined") {
          const res = await authenticate(credentials.username, credentials.password)
          if (typeof res !== "undefined") {
            return res
          } else {
            return null
          }
        } else {
          return null
        }
      },
      
    }),
  ],
  session: { strategy: "jwt" },
  callbacks: { jwt, session },
}

const handler = NextAuth(authOptions)

export { handler as GET, handler as POST }

function getCurrentEpochTime(): number {
  return Math.floor(Date.now() / 1000);
}
