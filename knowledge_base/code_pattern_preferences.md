# 🧩 Coding Pattern Preferences

Below are my core preferences and standards for coding within this project. Keep these in mind whenever writing or refactoring code:

1. **Always prefer simple solutions**  
   - 🟢 Strive for straightforward logic, minimizing complexity wherever possible.

2. **Avoid duplication of code**  
   - 🟢 Check if similar functionality already exists before writing new code.  
   - 🟢 Reuse or refactor existing code to keep the codebase lean.

3. **Account for different environments**  
   - 🟢 Ensure your code cleanly supports dev, test, and production environments.  
   - 🟢 This may involve reading or respecting environment variables, config files, etc.

4. **Only make requested or well-understood changes**  
   - 🟢 Do not introduce tangential modifications unless they’re relevant to the issue at hand.  
   - 🟢 Keep your scope small and focused.

5. **When fixing bugs, don’t introduce new patterns/tech unless necessary**  
   - 🟢 Exhaust all existing approaches first.  
   - 🟢 If a new pattern or technology must be introduced, remove the old implementation to avoid duplicate logic.

6. **Keep the codebase clean and organized**  
   - 🟢 Structure modules, functions, and classes thoughtfully.  
   - 🟢 Maintain consistent naming and folder organization.

7. **Avoid writing scripts inline if possible**  
   - 🟢 If a script is single-use or not essential to multiple features, keep it separate or ephemeral.  
   - 🟢 Prevent large, one-off scripts from cluttering the main code files.

8. **Refactor files over 200–300 lines of code**  
   - 🟢 Split large files into smaller modules for readability and maintainability.

9. **Mocking data is only for tests**  
   - 🟢 Don’t mock data in dev or prod code paths.  
   - 🟢 Real environment usage should rely on actual resources or test data that replicates production conditions.

10. **Never introduce stubbing/fake data in dev or prod**  

- 🟢 Stubs or fakes are strictly for testing.  
- 🟢 Production or dev environments should always handle real data sources.

11. **Never overwrite the `.env` file**  

- 🟢 Always confirm with the team before touching environment files.  
- 🟢 .env changes can break builds or modify sensitive configs, so proceed with caution.
