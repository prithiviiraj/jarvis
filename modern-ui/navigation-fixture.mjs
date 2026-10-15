// Exercise actual unified controls. No hidden legacy shell or synthetic navigation.
export async function settings(page){
 if(await page.getByRole('region',{name:'Living knowledge graph',exact:true}).isVisible().catch(()=>false))await page.getByRole('button',{name:'Home',exact:true}).click();
 if(!await page.locator('.settings-shell').isVisible().catch(()=>false)&&!await page.locator('.simple-settings').isVisible().catch(()=>false))await page.getByRole('button',{name:'Settings',exact:true}).click();
 if(await page.locator('.simple-settings').isVisible().catch(()=>false))await page.getByRole('button',{name:'Choose connection',exact:true}).click();
 const details=page.locator('.settings-nav details');if(await details.count()&&!await details.evaluate(e=>e.open))await details.locator('summary').click();
}
export async function team(page){await page.getByRole('button',{name:'Home',exact:true}).click();await page.getByLabel('Message draft',{exact:true}).waitFor();}
export async function conversation(page,expanded){const control=page.locator('.chat-expand-control');if((await control.getAttribute('aria-expanded'))!==String(expanded)){await page.getByRole('button',{name:'More',exact:true}).click();await page.getByRole('dialog',{name:'More options',exact:true}).getByRole('button',{name:expanded?'Expand conversation':'Collapse conversation',exact:true}).click();}}
export async function newChat(page){await page.getByRole('button',{name:'＋ New chat',exact:true}).click();}

export async function notes(page){await page.getByRole('button',{name:'More',exact:true}).click();await page.getByRole('dialog',{name:'More options',exact:true}).getByRole('button',{name:'My notes',exact:true}).click();await page.getByRole('region',{name:'Living knowledge graph'}).waitFor();}
export async function profile(page,name){await page.getByRole('combobox',{name:'Speaking profile',exact:true}).selectOption(name);}
