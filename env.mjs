import { z } from "zod"

const server = z.object({
    OPENAI_API_KEY: z.string("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"),
    GROQ_API_KEY: z.string().startsWith("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"),
    GOOGLE_API_KEY: z.string("AIzaSyAujSGhmFqbK7mWhaNrM_uFL9YNa8YTlQs"),
    DATABASE_URL: z.string().startsWith("postgresql://neondb_owner:m8W1sTwIxQMr@ep-square-boat-a5nlb7bq.us-east-2.aws.neon.tech/neondb?sslmode=require"),
    TAVILY_API_KEY: z.string().startsWith("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"),

    NODE_ENV: z.enum(["development", "test", "production"]),
})

const client = z.object({
    // client variables
})

/**
 * You can't destruct `process.env` as a regular object in the Next.js edge runtimes (e.g.
 * middlewares) or client-side so we need to destruct manually.
 *
 * @type {Record<keyof z.infer<typeof server> | keyof z.infer<typeof client>, string | undefined>}
 */

const processEnv = {
    OPENAI_API_KEY: process.env.OPENAI_API_KEY,
    GROQ_API_KEY: process.env.GROQ_API_KEY,
    GOOGLE_API_KEY: process.env.GOOGLE_API_KEY,
    DATABASE_URL: process.env.DATABASE_URL,
    TAVILY_API_KEY: process.env.TAVILY_API_KEY,

    NODE_ENV: process.env.NODE_ENV,
}

const merged = server.merge(client)

/** @typedef {z.input<typeof merged>} MergedInput */
/** @typedef {z.infer<typeof merged>} MergedOutput */
/** @typedef {z.SafeParseReturnType<MergedInput, MergedOutput>} MergedSafeParseReturn */

let env = /** @type {MergedOutput} */ (process.env)

if (!!process.env.SKIP_ENV_VALIDATION == false) {
    const isServer = typeof window === "undefined"

    const parsed = /** @type {MergedSafeParseReturn} */ (
        isServer
            ? merged.safeParse(processEnv) // on server we can validate all env vars
            : client.safeParse(processEnv) // on client we can only validate the ones that are exposed
    )

    if (parsed.success === false) {
        console.error(
            "❌ Invalid environment variables:",
            parsed.error.flatten().fieldErrors
        )
        throw new Error("Invalid environment variables")
    }

    env = new Proxy(parsed.data, {
        get(target, prop) {
            if (typeof prop !== "string") return undefined
            // Throw a descriptive error if a server-side env var is accessed on the client
            // Otherwise it would just be returning `undefined` and be annoying to debug
            if (!isServer && !prop.startsWith("NEXT_PUBLIC_"))
                throw new Error(
                    process.env.NODE_ENV === "production"
                        ? "❌ Attempted to access a server-side environment variable on the client"
                        : `❌ Attempted to access server-side environment variable '${prop}' on the client`
                )
            return target[/** @type {keyof typeof target} */ (prop)]
        },
    })
}

export { env }
