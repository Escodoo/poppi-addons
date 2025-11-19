**CFOP Configuration:**

1. Navigate to Fiscal > Configuration > CFOP
2. Select the CFOP that requires compensation
3. Enable "Use Compensation"
4. Configure the compensation parameters:
   
   * **Value Source**: Select how to calculate the compensation value:
     
     - Cost: Uses product's standard cost
     - Sale Price: Uses the invoice line unit price
     - Compensation Value: Uses the product's specific compensation value
   
   * **Debit Account Type**: Choose which account type receives the debit:
     
     - Asset Account: Debit goes to Asset, Credit goes to Liability
     - Liability Account: Debit goes to Liability, Credit goes to Asset
   
   * **Asset Account**: The asset account for compensation entries
   * **Liability Account**: The liability account for compensation entries
   * **Journal**: The journal where compensation entries will be posted

**Product Configuration:**

1. Navigate to Sales > Products > Products
2. Open a product that uses compensation
3. In the "Fiscal Compensation" tab:
   
   * Set the **Compensation Value** (used when Value Source = "Compensation Value")

**Automatic Compensation:**

When an invoice is posted:

1. The system checks if any invoice line has a CFOP with compensation enabled
2. For each eligible line, it calculates the compensation value based on the configured source
3. Creates a journal entry with:
   
   * Debit to the configured debit account (Asset or Liability)
   * Credit to the configured credit account (Liability or Asset)
   * Amount based on: quantity × selected value source

4. The compensation entry is automatically posted with reference to the original invoice

**Example Scenario:**

* CFOP 5.949 configured with:
  - Use Compensation: Yes
  - Value Source: Cost
  - Debit Account Type: Asset Account
  - Asset Account: "Goods in Transit"
  - Liability Account: "Compensation Payable"
  - Journal: "Compensation Journal"

* Product "Widget A" with Standard Cost = $100.00
* Invoice with 10 units of Widget A using CFOP 5.949

**Result**: Automatic journal entry created:
- Debit: Goods in Transit - $1,000.00
- Credit: Compensation Payable - $1,000.00