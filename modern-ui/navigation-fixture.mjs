// Renderer tests follow visible simplified navigation; no control is fabricated.
export async function settings(page){
 if(await page.getByRole('button',{name:'Explore tools',exact:true}).isVisible().catch(()=>false)){await page.getByRole('button',{name:'Explore tools',exact:true}).click();if(await page.getByRole('button',{name:'More settings',exact:true}).count())await page.getByRole('button',{name:'More settings',exact:true}).click();return}
 if(await page.locator('.settings-shell').isVisible().catch(()=>false))return;
 await page.getByRole('button',{name:'More',exact:true}).click();await page.getByRole('button',{name:'Settings',exact:true}).click();await page.getByRole('button',{name:'Explore tools',exact:true}).click();if(await page.getByRole('button',{name:'More settings',exact:true}).count())await page.getByRole('button',{name:'More settings',exact:true}).click();
}
export async function team(page){
 if(await page.getByLabel('Message draft',{exact:true}).isVisible().catch(()=>false))return;
 await page.getByRole('button',{name:'Previous view',exact:true}).click();
 if(!await page.getByLabel('Message draft',{exact:true}).isVisible().catch(()=>false))await page.getByRole('button',{name:'Previous view',exact:true}).click();
}
export async function conversation(page,expanded){
 await page.getByRole('button',{name:'More',exact:true}).click();await page.getByRole('button',{name:expanded?'Expand conversation':'Collapse conversation',exact:true}).click();
}
export async function newChat(page){
 await page.getByRole('button',{name:'More',exact:true}).click();await page.getByText('Notes and chats',{exact:true}).click();await page.getByRole('button',{name:'New chat',exact:true}).click();
}
