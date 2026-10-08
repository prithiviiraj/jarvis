"""Invoice data preparation only. No invented deal facts, tax advice, payment or delivery."""
from decimal import Decimal,InvalidOperation
from datetime import date
REQUIRED=('seller','buyer','invoice_number','issue_date','due_date','currency','items','tax_amount')
def amount(value):
 try:
  if not isinstance(value,str):raise ValueError()
  number=Decimal(value)
  if not number.is_finite()or number<0 or number.as_tuple().exponent<-2 or number>Decimal('100000000'):raise ValueError()
  return number
 except(InvalidOperation,ValueError):raise ValueError('Enter a nonnegative money amount as decimal text with up to2places')from None

def draft(facts):
 if not isinstance(facts,dict):raise ValueError('Use grounded invoice facts')
 missing=[k for k in REQUIRED if k not in facts or facts[k]in (None,'',[])]
 if missing:return {'state':'needs-details','missing':missing,'scope':'No invoice total or delivery inferred'}
 for k in ('seller','buyer','invoice_number'):
  if not isinstance(facts[k],str)or not 0<len(facts[k])<=300:raise ValueError('Invalid '+k)
 try:
  issue=date.fromisoformat(facts['issue_date']);due=date.fromisoformat(facts['due_date'])
  if due<issue:raise ValueError()
 except Exception:raise ValueError('Choose exact ISO issue/due dates; due cannot precede issue')from None
 if facts['currency']not in ('INR','USD','EUR','GBP'):raise ValueError('Choose an explicitly supported currency')
 if not isinstance(facts['items'],list)or not 1<=len(facts['items'])<=30:raise ValueError('Review1to30invoice items')
 subtotal=Decimal(0);items=[]
 for row in facts['items']:
  if not isinstance(row,dict)or not isinstance(row.get('description'),str)or not 0<len(row['description'])<=500 or type(row.get('quantity'))is not int or not 1<=row['quantity']<=10000:raise ValueError('Each item needs description, integer quantity and explicit unit price')
  unit=amount(row.get('unit_price'));total=unit*row['quantity'];subtotal+=total;items.append({'description':row['description'],'quantity':row['quantity'],'unit_price':format(unit,'.2f'),'line_total':format(total,'.2f')})
 tax=amount(facts['tax_amount']);total=subtotal+tax
 return {'state':'draft','invoice':{k:facts[k]for k in ('seller','buyer','invoice_number','issue_date','due_date','currency')},'items':items,'subtotal':format(subtotal,'.2f'),'tax_amount':format(tax,'.2f'),'total':format(total,'.2f'),'scope':'Owner-provided facts and decimal arithmetic only. Tax validity unverified. Draft not an issued invoice or payment request; delivery separately reviewed.'}
