"use strict";(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[5905],{15372:(e,t,n)=>{n.d(t,{A:()=>m});var o=n(66284),i=n(59860),r=n(14232),a=n(43181),s=n(66374);let c=(0,a.A)("label",{target:"enunibp0"})("padding:",s.A.spacing.tiny,";display:flex;align-items:center;flex-direction:column;position:relative;.input{&__input{outline:0;background:transparent;padding:",s.A.spacing.small,";transition:0.2s;transition-timing-function:ease;border:",e=>e.error?`1px solid ${s.A.color.ui.error}`:`1px solid ${s.A.color.ui.border}`,";border-radius:",s.A.radius.rounded,";z-index:",s.A.zIndex.elevated,";width:100%;color:",s.A.color.ui.primary,";&--icon{padding-left:40px;}&:hover{border-color:",s.A.color.ui.secondary,";}&:focus{border-color:",s.A.color.ui.primary,";}&:disabled{background:",s.A.color.ui.background,";color:",s.A.color.text.tertiary,";}&::placeholder{color:",s.A.color.text.tertiary,";font-size:",s.A.fontSize.caption,";}}&__label-wrapper{display:flex;align-items:center;height:20px;position:absolute;left:10px;bottom:18px;}&__icon-wrapper{height:20px;width:20px;margin-right:",s.A.spacing.small,";z-index:",s.A.zIndex.elevated,";}&__label{position:relative;bottom:22px;padding:0 ",s.A.spacing.tiny,";color:",s.A.color.text.primary,";background-color:",s.A.color.ui.foreground,";font-size:",s.A.fontSize.footnote,";font-weight:",s.A.fontWeight.bold,";z-index:",s.A.zIndex.elevated,";&--icon{right:32px;}}&__input:placeholder-shown+.input__label-wrapper .input__label{display:none;}&__input:active+.input__label-wrapper .input__label{display:block;}&__input:focus+.input__label-wrapper .input__label{display:block;}}");var l=n(37876);let d=["type","className","placeholder","label","input","icon","meta"];function p(e,t){var n=Object.keys(e);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);t&&(o=o.filter(function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable})),n.push.apply(n,o)}return n}function b(e){for(var t=1;t<arguments.length;t++){var n=null!=arguments[t]?arguments[t]:{};t%2?p(Object(n),!0).forEach(function(t){(0,o.A)(e,t,n[t])}):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(n)):p(Object(n)).forEach(function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(n,t))})}return e}let m=(0,r.forwardRef)(function(e,t){let{type:n,className:o,placeholder:r,label:a,input:p={},icon:m,meta:g}=e,u=(0,i.A)(e,d),f=!!m,h=f&&m,x=["input__input",f&&"input__input--icon"].filter(Boolean).join(" "),_=["input__label",f&&"input__label--icon"].filter(Boolean).join(" ");return(0,l.jsxs)(c,{className:o,iconExists:f,error:!!g?.touched&&!!g?.error,children:[(0,l.jsx)("input",b(b({ref:t,className:x,type:n,placeholder:g?.active?"":r},p),u)),(0,l.jsxs)("div",{className:"input__label-wrapper",children:[h&&(0,l.jsx)("div",{className:"input__icon-wrapper",children:(0,l.jsx)(h,{fill:s.A.color.ui.secondary,height:20,width:20})}),(0,l.jsx)("span",{className:_,children:a||r})]})]})})},18925:(e,t,n)=>{n.d(t,{A:()=>s});var o=n(81777),i=n(56619),r=n(40474),a=n(25896);let s=()=>{let[{dateOfBirth:e}]=r.A.useContainer(),t=(0,a.h)(),n=21;if(e){let t=(0,o.qg)(e,"yyyyMMdd",new Date);n=(0,i.V)(new Date,t)}return{age:n,darkMode:t}}},30268:(e,t,n)=>{n.d(t,{A:()=>s});var o=n(43181),i=n(57558),r=n(37876);let a=(0,o.A)(i.A,{target:"e1ji50wr0"})("position:",e=>e.cardMode?"absolute":"static",";top:0;bottom:0;left:0;width:100%;height:100%;border:0;object-fit:cover;"),s=({title:e,image:t,cardMode:n=!1,className:o="",isLazy:i=!1,fetchPriority:s})=>{if(!t)return n?(0,r.jsx)("img",{style:{objectFit:"cover"},className:"embed-responsive-item placeholder",alt:"placeholder",src:"#"}):null;let c=`${e} article feature image`;return n?(0,r.jsx)(a,{cardMode:n,image:t,alt:c,width:1200,height:675,sizes:"(max-width: 900px) 100vw, 60vw",mobile:{image:t,width:800,height:450},isLazy:!1,fetchPriority:s}):(0,r.jsx)(a,{className:o,image:t,alt:c,width:1200,height:675,sizes:"(max-width: 900px) 100vw, 60vw",mobile:{image:t,width:800,height:450},isLazy:i,fetchPriority:s})}},33187:(e,t,n)=>{n.d(t,{A:()=>d});var o=n(66724),i=n(77446),r=n(40474),a=n(43181),s=n(66374);let c=(0,a.A)("div",{target:"e16xo8w20"})("margin:0 auto;margin-top:",e=>e.showTopMargin?s.A.spacing.medium:0,";min-height:82px;display:block;max-width:1400px;@media (max-width: ",s.A.media.mobile,"){margin-top:0;min-height:129px;}");var l=n(37876);let d=({placementSlug:e,filters:t,context:n="",className:a="",showTopMargin:s,placementId:d})=>{let[{stateCode:p}]=i.A.useContainer(),[{isLoggedIn:b,subscriptionTier:m,wasPro:g,trackedParentBookIds:u}]=r.A.useContainer();return(0,l.jsx)(c,{showTopMargin:s,className:a,"data-testid":"affiliate-banner",children:(0,l.jsx)(o.A,{placementType:e,placementId:d,context:n,location:p,league:t?.league||"",isLoggedIn:b,subscriptionTier:m,wasPro:g,pageSlug:t?.page_slug||"",userParentBookIds:u||[],sponsorSlug:t?.sponsor_slug||"",internalId:t?.internal_id||""})})}},52361:(e,t,n)=>{n.d(t,{k:()=>g});var o=n(66284),i=n(14232),r=n(98444),a=n(77446),s=n(39273),c=n(40474),l=n(99373),d=n(80672);function p(e,t){var n=Object.keys(e);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);t&&(o=o.filter(function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable})),n.push.apply(n,o)}return n}function b(e){for(var t=1;t<arguments.length;t++){var n=null!=arguments[t]?arguments[t]:{};t%2?p(Object(n),!0).forEach(function(t){(0,o.A)(e,t,n[t])}):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(n)):p(Object(n)).forEach(function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(n,t))})}return e}let m=e=>Object.keys(e).map(t=>({value:t,display:e[t]}));function g(e){let t=(0,i.useRef)(!1),[{stateCode:n},o]=a.A.useContainer(),[{user:p,token:g,appSettings:u,isLoggedIn:f},h]=c.A.useContainer(),{id:x}=p,_=(0,i.useMemo)(()=>(0,l.Pr)(h,{userId:x,token:g}),[h,x,g]),y=(0,i.useMemo)(()=>!t.current&&e||n,[e,n]);return{selectedLocation:y,handleDropdownChange:e=>{if(o((0,s.N)(e.value)),"world"!==e.value){if(!f)return void(0,d.TV)("location",e.value,{"max-age":604800});_({app_settings:b(b({},u),{},{location:e.value})},{onSuccess:()=>{(0,d.TV)("location",e.value,{"max-age":604800}),u.location=e.value}})}t.current=!0},locations:r.LP[y]?m(r.LP):m(r.iq)}}},66724:(e,t,n)=>{n.d(t,{A:()=>l});var o=n(66284),i=n(18925),r=n(55394),a=n(37876);function s(e,t){var n=Object.keys(e);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);t&&(o=o.filter(function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable})),n.push.apply(n,o)}return n}function c(e){for(var t=1;t<arguments.length;t++){var n=null!=arguments[t]?arguments[t]:{};t%2?s(Object(n),!0).forEach(function(t){(0,o.A)(e,t,n[t])}):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(n)):s(Object(n)).forEach(function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(n,t))})}return e}let l=e=>{let t=e.placementId||(0,r.J1)(e.placementType||"global"),n=(0,i.A)(),o=c(c({},e),n),s={"affiliate-id":o.affiliateId||void 0,"affiliate-type":o.affiliateType||void 0,affiliate:o.affiliate||void 0,age:o.age||void 0,context:o.context,"dark-mode":o.darkMode||void 0,"data-testid":"bam-banner","hide-underage":o.hideUnderage||void 0,"internal-id":o.internalId||void 0,"is-logged-in":o.isLoggedIn||void 0,league:o.league||void 0,location:(0,r.MC)(o.location),"placement-id":t,"property-id":1,"sponsor-slug":o.sponsorSlug||void 0,"subscription-tier":o.subscriptionTier||void 0,"user-parent-book-ids":o.userParentBookIds?o.userParentBookIds.join(","):void 0,"was-pro":o.wasPro||void 0};return(0,a.jsxs)("div",{children:[(0,a.jsx)("div",{dangerouslySetInnerHTML:{__html:`
            <style sty-id="sc-bam-banner">
      /*!@:host*/
      .sc-bam-banner-h {
        width: 100%;
      }</style>
      <style sty-id="sc-banner-component">
      /*!@:host*/
      .sc-banner-component-h {
        display: block;
      } /*!@.age-blur*/
      .age-blur.sc-banner-component {
        filter: blur(0.75rem);
      }</style><style sty-id="sc-static-banner-component">
      /*!@:host*/
      .sc-static-banner-component-h {
        display: block;
      } /*!@.font*/
      .font.sc-static-banner-component {
        font-family: var(--font-family);
        color: var(--color-foreground);
      } /*!@.item*/
      .item.sc-static-banner-component {
        color: var(--color-foreground);
        box-sizing: border-box;
        min-height: 82px;
        background: radial-gradient(
            100% 100% at 50% 50%,
            rgba(0, 0, 0, 0) 0%,
            rgba(0, 0, 0, 0) 30%,
            rgba(0, 0, 0, 0.3) 100%

          ),
          linear-gradient(90deg, #00000022 0%, #00000000 30%),
          linear-gradient(270deg, #00000011 0%, #00000000 30%);
        text-decoration: none;
        overflow: hidden;
        border-radius: var(--border-medium);
        padding: var(--spacing-tiny);
        align-items: center;
        display: grid;
        gap: var(--spacing-small);
        grid-template-columns: 35px 1fr 100px;
        grid-template-areas: "logo cta bonus" 
"terms terms terms";
      } /*!@.item__logo*/
      .item__logo.sc-static-banner-component {
        width: 35px;
        height: 35px;
        border-radius: var(--border-small);
      } /*!@.item__logo-skeleton*/
      .item__logo-skeleton.sc-static-banner-component {
        width: 35px;
        height: 35px;
        border-radius: var(--border-small);
        background-color: #ffffff33;
      } /*!@.item__cta*/
      .item__cta.sc-static-banner-component {
        display: flex;
        flex-direction: column;
        grid-area: cta;
        align-self: center;
        font-weight: 800;
        font-size: 14px;
        line-height: var(--spacing-smedium);
        padding: 0;
      } /*!@.item__cta-skeleton*/
      .item__cta-skeleton.sc-static-banner-component {
        width: 100%;
        height: 16px;
        background-color: #ffffff33;
      } /*!@.item__terms*/
      .item__terms.sc-static-banner-component {
        background-color: #ffffff33;
        padding: var(--spacing-tiny);
        align-self: stretch;
        border-radius: var(--border-small);
        display: flex;
        align-items: center;
        font-size: 9px;
        grid-area: terms;
      } /*!@.bonus*/
      .bonus.sc-static-banner-component {
        flex: 0 1 100px;
        border: 1px dashed var(--color-border);
        border-radius: var(--border-small);
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        line-height: var(--spacing-smedium);
        padding: var(--spacing-tiny);
        background-color: var(--color-white-transparent);
        grid-area: bonus;
      } /*!@.bonus:hover*/
      .bonus.sc-static-banner-component:hover {
        background-color: #ffffff55;
        border: 1px dashed var(--color-secondary);
      } /*!@.bonus-code*/
      .bonus-code.sc-static-banner-component {
        font-size: var(--font-size-subcaption);
        font-weight: 800;
      } /*!@.bonus-text*/
      .bonus-text.sc-static-banner-component {
        font-size: var(--font-size-caption);
        font-weight: 800;
        font-size: 9px;
      } /*!@.bonus-copy*/
      .bonus-copy.sc-static-banner-component {
        font-size: var(--font-size-subcaption);
        font-weight: 800;
      } /*!@.no-code*/
      .no-code.sc-static-banner-component {
        font-size: var(--font-size-subcaption);
        font-weight: 800;
        line-height: var(--spacing-smedium);
      } /*!@.skeleton-item__logo*/
      .skeleton-item__logo.sc-static-banner-component {
        width: 35px;
        height: 35px;
        border-radius: var(--border-small);
        align-self: center;
        background-color: var(--color-background);
        animation: var(--loading);
      } /*!@.skeleton-item__description*/
      .skeleton-item__description.sc-static-banner-component {
        flex-grow: 1;
        gap: 2px;
      } /*!@.skeleton-item__description > *:nth-of-type(odd)*/
      .skeleton-item__description.sc-static-banner-component
        > *.sc-static-banner-component:nth-of-type(odd) {
        height: var(--font-size-caption);
        width: 75px;
        background-color: var(--color-background);
        animation: var(--loading);
      } /*!@.skeleton-item__description > *:nth-of-type(even)*/
      .skeleton-item__description.sc-static-banner-component
        > *.sc-static-banner-component:nth-of-type(even) {
        height: var(--font-size-subcaption);
        width: 100%;
        margin-top: 2px;
        margin-bottom: 2px;
        background-color: var(--color-background);
        animation: var(--loading);
      } /*!@.skeleton-button*/
      .skeleton-button.sc-static-banner-component {
        background-color: var(--color-background);
        animation: var(--loading);
      }
      @media (min-width: 576px) {
        /*!@.item*/
        .item.sc-static-banner-component {
          background: radial-gradient(
              100% 100% at 50% 50%,
              rgba(255, 255, 255, 0) 0%,
              rgba(255, 255, 255, 0) 30%,
              rgba(0, 0, 0, 0.3) 100%
            ),
            linear-gradient(90deg, #000000aa 0%, #00000022 70%);
          grid-template-columns: 50px auto auto 100px;
          grid-template-areas: "logo cta terms bonus";
          padding: var(--spacing-small);
        } /*!@.item__logo*/
        .item__logo.sc-static-banner-component {
          width: 35px;
          height: 35px;
        } /*!@.item__logo-skeleton*/
        .item__logo-skeleton.sc-static-banner-component {
          width: 50px;
          height: 50px;
        } /*!@.item__cta*/
        .item__cta.sc-static-banner-component {
          line-height: var(--spacing-medium);
          font-size: 20px;
        } /*!@.item__cta-skeleton*/
        .item__cta-skeleton.sc-static-banner-component {
          height: 20px;
        } /*!@.item__terms*/
        .item__terms.sc-static-banner-component {
          width: fit-content;
          justify-self: end;
          margin-left: 50px;
          font-size: 11px;
        } /*!@.bonus*/
        .bonus.sc-static-banner-component {
          padding: var(--spacing-small);
        }
      }
      </style>
            `}}),(0,a.jsx)("bam-banner",c(c({},s),{},{className:"sc-bam-banner-h hydrated","s-id":"1",dangerouslySetInnerHTML:{__html:`<!--r.1--><banner-component
        class="sc-bam-banner sc-banner-component-h hydrated"
        c-id="1.0.0.0"
        s-id="2"
        ><!--r.2-->
        <div class="sc-banner-component" c-id="2.0.0.0">
          <static-banner-component
            class="sc-banner-component sc-static-banner-component-h hydrated"
            c-id="2.1.1.0"
            s-id="3"
            ><!--r.3--><a
              rel="nofollow noopener"
              class="item font sc-static-banner-component"
              href="#"
              c-id="3.0.0.0"
              style="background-color: #cccccc"
              ><lazy-load-logo
                class="item__logo sc-static-banner-component hydrated"
                c-id="3.1.1.0"
                s-id="4"
                ><!--r.4--><picture c-id="4.0.0.0"
                  ><source
                    srcset="
                      https://assets.actionnetwork.com/113x113/816137_square-xxl.webp 113w,
                      https://assets.actionnetwork.com/150x150/816137_square-xxl.webp 150w,
                      https://assets.actionnetwork.com/225x225/816137_square-xxl.webp 225w,
                      https://assets.actionnetwork.com/300x300/816137_square-xxl.webp 300w,
                      https://assets.actionnetwork.com/450x450/816137_square-xxl.webp 450w,
                      https://assets.actionnetwork.com/900x900/816137_square-xxl.webp 900w
                    "
                    type="image/webp"
                    c-id="4.1.1.0" />
                  <img
                    class="lazy-logo image"
                    sizes="150px"
                    width="35"
                    height="35"
                    src="https://assets.actionnetwork.com/816137_square-xxl.png"
                    alt="promotion logo"
                    c-id="4.2.1.1" /></picture
              ></lazy-load-logo>
              <div class="item__cta sc-static-banner-component" c-id="3.2.1.1">
                <span class="font sc-static-banner-component" c-id="3.3.2.0"
                  ><!--t.3.4.3.0-->Turn your sports knowledge into winning
                  predictions</span
                >
              </div>
              <div
                class="item__terms sc-static-banner-component"
                c-id="3.5.1.2"
              >
                <span
                  class="item__terms-font font sc-static-banner-component"
                  c-id="3.6.2.0"><!--t.3.7.3.0-->21+ or 18+ in Certain Locations. 19+ in ON. Please Play Responsibly. Gambling Problem? Call 1-800-GAMBLER. Visit connexontario.ca or Call 1-866-531-2600 in ON.</span>
              </div>
              <div
                class="bonus no-code bam-no-code sc-static-banner-component"
                c-id="3.8.1.3"
              >
                <!--t.3.9.2.0-->No Code Needed
              </div></a
            ></static-banner-component>
        </div></banner-component>`}}))]})}},71005:(e,t,n)=>{n.d(t,{A:()=>l});var o=n(18975),i=n(98859),r=n(43181),a=n(66374);let s=(0,r.A)("div",{target:"eongx2y0"})("cursor:pointer;justify-self:center;& .cta-button{display:flex;align-items:center;justify-content:center;width:44px;height:44px;padding:",a.A.spacing.tiny,";background-color:",a.A.color.ui.background,";border-radius:50%;}@media (max-width: ",a.A.media.mobile,"){grid-row:1/2;grid-column:3/3;}");var c=n(37876);let l=({handleClose:e,i13n:t})=>(0,c.jsx)(s,{children:(0,c.jsx)(o.A,{className:"cta-button",onClick:()=>e(t),shape:"pill",children:(0,c.jsx)(i.A,{width:18,height:18,fill:a.A.color.ui.secondary})})})}}]);